"""Tests for samples/robot_face_animation2.py."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from PIL import Image

# samples ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "samples"))

from robot_face_animation2 import (  # type: ignore[import-not-found]
    MOODS,
    FaceState,
    FaceStateParser,
    RobotFace,
    RobotFaceApp,
    lerp,
    main,
)

# ===========================================================================
# FaceState テスト
# ===========================================================================


class TestFaceState:
    """Tests for FaceState dataclass."""

    def test_default_values(self):
        """デフォルト値のテスト."""
        state = FaceState()
        assert state.mouth_curve == 0
        assert state.brow_tilt == 0
        assert state.mouth_open == 0
        assert state.left_eye_openness == 1.0
        assert state.left_eye_size == 8.0
        assert state.left_eye_curve == 0.0
        assert state.right_eye_openness == 1.0
        assert state.right_eye_size == 8.0
        assert state.right_eye_curve == 0.0

    def test_copy(self):
        """copy() メソッドのテスト."""
        original = FaceState(mouth_curve=10, brow_tilt=5)
        copied = original.copy()

        assert copied.mouth_curve == original.mouth_curve
        assert copied.brow_tilt == original.brow_tilt
        # 独立したインスタンスであることを確認
        copied.mouth_curve = 20
        assert original.mouth_curve == 10

    def test_custom_values(self):
        """カスタム値のテスト."""
        state = FaceState(
            mouth_curve=15,
            brow_tilt=-10,
            mouth_open=0.5,
            left_eye_openness=0.0,
            left_eye_size=6.0,
            left_eye_curve=1.0,
        )
        assert state.mouth_curve == 15
        assert state.brow_tilt == -10
        assert state.mouth_open == 0.5
        assert state.left_eye_openness == 0.0
        assert state.left_eye_size == 6.0
        assert state.left_eye_curve == 1.0


# ===========================================================================
# lerp テスト
# ===========================================================================


class TestLerp:
    """Tests for lerp() function."""

    def test_lerp_start(self):
        """t=0 で開始値を返す."""
        assert lerp(0, 10, 0) == 0

    def test_lerp_end(self):
        """t=1 で終了値を返す."""
        assert lerp(0, 10, 1) == 10

    def test_lerp_middle(self):
        """t=0.5 で中間値を返す."""
        assert lerp(0, 10, 0.5) == 5

    def test_lerp_negative(self):
        """負の値での補間."""
        assert lerp(-10, 10, 0.5) == 0


# ===========================================================================
# FaceStateParser テスト
# ===========================================================================


class TestFaceStateParser:
    """Tests for FaceStateParser class."""

    @pytest.fixture
    def parser(self):
        """FaceStateParser インスタンス."""
        return FaceStateParser()

    def test_parse_neutral(self, parser):
        """ニュートラル顔 _O_O のパース."""
        state = parser.parse_face_string("_O_O")
        assert state.brow_tilt == 0
        assert state.left_eye_openness == 1.0
        assert state.left_eye_size == 8.0
        assert state.right_eye_openness == 1.0
        assert state.right_eye_size == 8.0
        assert state.mouth_curve == 0

    def test_parse_happy(self, parser):
        """笑顔 _O^O のパース."""
        state = parser.parse_face_string("_OvO")
        assert state.mouth_curve == 15  # v は笑顔

    def test_parse_sad(self, parser):
        """悲しい顔 _O^O のパース."""
        state = parser.parse_face_string("_O^O")
        assert state.mouth_curve == -10  # ^ は悲しい顔

    def test_parse_angry_brow(self, parser):
        """怒り眉毛 /O_O のパース."""
        state = parser.parse_face_string("/O_O")
        assert state.brow_tilt == 25  # / は怒り眉

    def test_parse_sad_brow(self, parser):
        r"""悲しい眉毛 \O_O のパース."""
        state = parser.parse_face_string("\\O_O")
        assert state.brow_tilt == -10  # \ は悲しい眉

    def test_parse_closed_eyes(self, parser):
        """閉じた目 _-_- のパース."""
        state = parser.parse_face_string("_-_-")
        assert state.left_eye_openness == 0.0
        assert state.right_eye_openness == 0.0

    def test_parse_small_eyes(self, parser):
        """小さい目 _o_o のパース."""
        state = parser.parse_face_string("_o_o")
        assert state.left_eye_size == 6.0
        assert state.right_eye_size == 6.0

    def test_parse_curved_closed_eyes(self, parser):
        """にこにこ目 _^_^ のパース."""
        state = parser.parse_face_string("_^_^")
        assert state.left_eye_openness == 0.0
        assert state.left_eye_curve == 1.0
        assert state.right_eye_openness == 0.0
        assert state.right_eye_curve == 1.0

    def test_parse_open_mouth(self, parser):
        """開いた口 _OO のパース."""
        state = parser.parse_face_string("_OOO")
        assert state.mouth_open == 1.1

    def test_parse_invalid_length(self, parser):
        """4文字以外はエラー."""
        with pytest.raises(ValueError, match="4 characters"):
            parser.parse_face_string("_O_")

        with pytest.raises(ValueError, match="4 characters"):
            parser.parse_face_string("_O_O_")


# ===========================================================================
# RobotFace テスト
# ===========================================================================


class TestRobotFace:
    """Tests for RobotFace class."""

    @pytest.fixture
    def robot_face(self):
        """RobotFace インスタンス."""
        return RobotFace(FaceState(), size=240)

    def test_init(self, robot_face):
        """初期化テスト."""
        assert robot_face.size == 240
        assert robot_face.current_gaze_x == 0.0
        assert robot_face.target_gaze_x == 0.0
        assert robot_face.is_changing is False

    def test_set_gaze(self, robot_face):
        """視線設定テスト."""
        robot_face.set_gaze(10.0)
        assert robot_face.target_gaze_x == 10.0

    def test_set_target_state(self, robot_face):
        """ターゲット状態設定テスト."""
        new_state = FaceState(mouth_curve=15)
        robot_face.set_target_state(new_state, duration=0.5)

        assert robot_face.target_state.mouth_curve == 15
        assert robot_face.is_changing is True

    def test_update_gaze(self, robot_face):
        """update() での視線補間テスト."""
        robot_face.set_gaze(10.0)
        robot_face.update()

        # lerp(0, 10, 0.8) = 8.0
        assert robot_face.current_gaze_x == 8.0

    def test_update_state(self, robot_face):
        """update() での状態補間テスト."""
        new_state = FaceState(mouth_curve=20)
        robot_face.set_target_state(new_state, duration=0.001)

        # 少し待ってから更新
        time.sleep(0.01)
        robot_face.update()

        # 変化が完了しているはず
        assert robot_face.is_changing is False
        assert robot_face.current_state.mouth_curve == 20

    def test_draw_returns_image(self, robot_face):
        """draw() が PIL Image を返す."""
        img = robot_face.draw(320, 240, (0, 0, 0))

        assert isinstance(img, Image.Image)
        assert img.size == (320, 240)

    def test_is_changing_property(self, robot_face):
        """is_changing プロパティのテスト."""
        assert robot_face.is_changing is False

        robot_face.set_target_state(FaceState(mouth_curve=10), duration=1.0)
        assert robot_face.is_changing is True


# ===========================================================================
# RobotFaceApp テスト
# ===========================================================================


class TestRobotFaceApp:
    """Tests for RobotFaceApp class."""

    @pytest.fixture
    def mock_output(self):
        """Mock DisplayOutput."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def robot_face_app(self, mock_output):
        """RobotFaceApp インスタンス."""
        return RobotFaceApp(
            output=mock_output,
            screen_width=320,
            screen_height=240,
            bg_color="black",
            all_moods=MOODS,
            face_change_duration=0.5,
            init_mood="neutral",
        )

    def test_init(self, robot_face_app):
        """初期化テスト."""
        assert robot_face_app.screen_width == 320
        assert robot_face_app.screen_height == 240
        assert robot_face_app.bg_color == "black"
        assert robot_face_app.face is not None

    def test_handle_gaze_update(self, robot_face_app):
        """_handle_gaze_update() のテスト."""
        # 次の gaze 更新時間を過去に設定
        robot_face_app._next_gaze_time = 0

        with patch("random.uniform", side_effect=[10.0, 1.0]):
            robot_face_app._handle_gaze_update(time.time())

        assert robot_face_app.face.target_gaze_x == 10.0

    def test_handle_random_mood_update(self, robot_face_app):
        """_handle_random_mood_update() のテスト."""
        # 次の mood 更新時間を過去に設定
        robot_face_app._next_mood_time = 0

        with patch("random.choice", return_value="happy"):
            with patch("random.uniform", side_effect=[1.0, 3.0]):
                robot_face_app._handle_random_mood_update(time.time())

        assert (
            robot_face_app.face.target_state.mouth_curve == 15
        )  # happy の値

    def test_end(self, robot_face_app, mock_output):
        """end() のテスト."""
        robot_face_app.end()
        mock_output.close.assert_called_once()


# ===========================================================================
# CLI テスト
# ===========================================================================


class TestMainCLI:
    """Tests for main() CLI command."""

    def test_help(self):
        """--help オプションのテスト."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "--random" in result.output
        assert "--debug" in result.output

    @patch("robot_face_animation2.create_output_device")
    @patch("time.sleep")
    def test_sequence_mode(self, mock_sleep, mock_create_output):
        """シーケンスモードのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        # time.sleep で KeyboardInterrupt を発生させてループを止める
        mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

        runner = CliRunner()
        result = runner.invoke(main, ["_O_O", "/O_O"])

        # KeyboardInterrupt で終了
        assert result.exit_code == 0
        assert mock_output.close.called

    @patch("robot_face_animation2.create_output_device")
    @patch("time.sleep")
    def test_random_mode(self, mock_sleep, mock_create_output):
        """ランダムモードのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

        runner = CliRunner()
        result = runner.invoke(main, ["--random"])

        assert result.exit_code == 0
        assert mock_output.close.called
