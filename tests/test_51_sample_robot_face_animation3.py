import time
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from PIL import Image  # PIL.Image をインポート

from samples.robot_face_animation3 import (
    ANIMATION,
    BROW_MAP,
    COLORS,
    EYE_MAP,
    LAYOUT,
    MOODS_STR,
    MOUTH_MAP,
    FaceConfig,
    FaceMode,
    FaceState,
    FaceStateParser,
    RobotFace,
    RobotFaceApp,
    lerp,
)

# main 関数もインポート
from samples.robot_face_animation3 import main as robot_face_animation3_main


class TestLerp:
    """lerp ヘルパー関数のテスト"""

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


class TestFaceState:
    """FaceState データクラスのテスト"""

    def test_default_values(self):
        """デフォルト値が正しく設定されているか."""
        state = FaceState()
        assert state.mouth_curve == 0
        assert state.brow_tilt == 0
        assert state.mouth_open == 0
        assert state.left_eye_openness == 1.0
        assert state.right_eye_openness == 1.0

    def test_custom_values(self):
        """カスタム値が正しく設定されているか."""
        state = FaceState(mouth_curve=10, brow_tilt=-5, left_eye_openness=0.5)
        assert state.mouth_curve == 10
        assert state.brow_tilt == -5
        assert state.left_eye_openness == 0.5
        assert state.mouth_open == 0

    def test_copy(self):
        """コピーが元のオブジェクトに影響しないか."""
        original = FaceState(mouth_curve=10)
        copied = original.copy()
        copied.mouth_curve = 20
        assert original.mouth_curve == 10
        assert copied.mouth_curve == 20


class TestFaceStateParser:
    """FaceStateParser のテスト"""

    @pytest.fixture
    def parser(self):
        """FaceStateParser インスタンス."""
        return FaceStateParser(BROW_MAP, EYE_MAP, MOUTH_MAP)

    def test_parse_neutral(self, parser):
        """_OO_ の解析."""
        state = parser.parse_face_string("_OO_")
        assert state.brow_tilt == 0
        assert state.left_eye_openness == 1.0
        assert state.right_eye_openness == 1.0
        assert state.mouth_curve == 0
        assert state.mouth_open == 0

    def test_parse_happy(self, parser):
        """_OOv の解析."""
        state = parser.parse_face_string("_OOv")
        assert state.mouth_curve == 15
        assert state.mouth_open == 0

    def test_parse_sad(self, parser):
        """^oo^ の解析."""
        state = parser.parse_face_string("^oo^")
        assert state.mouth_curve == -10
        assert state.brow_tilt == -10
        assert state.left_eye_size == 6.0

    def test_parse_angry_brow(self, parser):
        """voo^ (怒った眉) の解析."""
        state = parser.parse_face_string("voo^")
        assert state.brow_tilt == 25

    def test_parse_sad_brow(self, parser):
        """^oo^ (悲しい眉) の解析."""
        state = parser.parse_face_string("^oo^")
        assert state.brow_tilt == -10

    def test_parse_small_eyes(self, parser):
        """_oo_ (小さい目) の解析."""
        state = parser.parse_face_string("_oo_")
        assert state.left_eye_size == 6.0
        assert state.right_eye_size == 6.0

    def test_parse_closed_eyes(self, parser):
        """_--_ (閉じた目) の解析."""
        state = parser.parse_face_string("___v")
        assert state.left_eye_openness == 0.0
        assert state.right_eye_openness == 0.0

    def test_parse_curved_closed_eyes(self, parser):
        """_vv_ (への字の閉じた目) の解析."""
        state = parser.parse_face_string("_vv_")
        assert state.left_eye_curve == -1.0
        assert state.right_eye_curve == -1.0

    def test_parse_open_mouth(self, parser):
        """_OOO (開いた口) の解析."""
        state = parser.parse_face_string("_OOO")
        assert state.mouth_open == 1.1

    def test_parse_invalid_length(self, parser):
        """不正な長さの文字列の解析."""
        with pytest.raises(ValueError):
            parser.parse_face_string("TOO_SHORT")
        with pytest.raises(ValueError):
            parser.parse_face_string("LONG__STRING")


class TestRobotFace:
    """RobotFace クラスのテスト"""

    @pytest.fixture
    def robot_face(self):
        """RobotFace インスタンス."""
        return RobotFace(initial_state=FaceState())

    def test_init(self, robot_face):
        """初期化のテスト."""
        assert isinstance(robot_face.animator.current_state, FaceState)
        assert robot_face.animator.current_state.mouth_curve == 0
        assert robot_face.animator.current_gaze_x == 0.0

    def test_set_target_state(self, robot_face):
        """set_target_state のテスト."""
        new_state = FaceState(mouth_curve=10)
        robot_face.set_target_state(new_state)
        assert robot_face.animator.target_state.mouth_curve == 10
        assert robot_face.is_changing is True

    def test_update_state(self, robot_face):
        """update メソッドによる状態更新のテスト."""
        initial_state = robot_face.animator.current_state.copy()
        new_state = FaceState(mouth_curve=10)
        robot_face.set_target_state(new_state, duration=0.1)

        time.sleep(0.05)  # アニメーション中に更新
        robot_face.update()
        assert (
            robot_face.animator.current_state.mouth_curve
            > initial_state.mouth_curve
        )
        assert (
            robot_face.animator.current_state.mouth_curve
            < new_state.mouth_curve
        )

        time.sleep(0.1)  # アニメーション完了後に更新
        robot_face.update()
        assert (
            robot_face.animator.current_state.mouth_curve
            == new_state.mouth_curve
        )
        assert robot_face.is_changing is False

    def test_set_gaze(self, robot_face):
        """set_gaze のテスト."""
        robot_face.set_gaze(5.0)
        assert robot_face.animator.target_gaze_x == 5.0

    def test_update_gaze(self, robot_face):
        """update メソッドによる視線更新のテスト."""
        robot_face.set_gaze(5.0)
        robot_face.update()
        assert robot_face.animator.current_gaze_x > 0.0
        assert robot_face.animator.current_gaze_x < 5.0

    def test_is_changing_property(self, robot_face):
        """is_changing プロパティのテスト."""
        assert robot_face.is_changing is False
        robot_face.set_target_state(FaceState(mouth_curve=10), duration=0.1)
        assert robot_face.is_changing is True
        time.sleep(0.2)
        robot_face.update()
        assert robot_face.is_changing is False

    def test_draw_returns_image(self, robot_face):
        """draw メソッドが PIL.Image を返すか."""
        img = robot_face.draw(320, 240, (0, 0, 0))
        assert isinstance(img, Image.Image)
        assert img.size == (320, 240)


class TestRobotFaceApp:
    """RobotFaceApp クラスのテスト"""

    @pytest.fixture
    def mock_output(self):
        """モックの DisplayOutput オブジェクト."""
        mock = MagicMock()
        mock.show.return_value = None
        mock.close.return_value = None
        return mock

    @pytest.fixture
    def robot_face_app(self, mock_output):
        """RobotFaceApp インスタンス."""
        # ダミーのFaceModeインスタンスを作成
        dummy_mode = MagicMock(spec=FaceMode)  # FaceMode のモック
        dummy_mode.run.return_value = (
            None  # run メソッドが呼ばれても何もしない
        )

        face_config = FaceConfig(
            moods_str=MOODS_STR,
            brow_map=BROW_MAP,
            eye_map=EYE_MAP,
            mouth_map=MOUTH_MAP,
            layout_config=LAYOUT,
            color_config=COLORS,
            animation_config=ANIMATION,
        )

        return RobotFaceApp(
            output=mock_output,
            screen_width=320,
            screen_height=240,
            bg_color="black",
            mode=dummy_mode,  # ここで mode を渡す
            face_config=face_config,
        )

    def test_init(self, robot_face_app, mock_output):
        """初期化のテスト."""
        assert robot_face_app.output == mock_output
        assert isinstance(robot_face_app.face, RobotFace)
        assert isinstance(robot_face_app.parser, FaceStateParser)
        assert (
            robot_face_app.current_mode.run.called is False
        )  # main() がまだ呼ばれてないので

    def test_render_frame(self, robot_face_app, mock_output):
        """render_frame メソッドのテスト."""
        robot_face_app.render_frame()
        mock_output.show.assert_called_once()
        # show メソッドが PIL.Image オブジェクトで呼び出されたことを確認
        assert isinstance(mock_output.show.call_args[0][0], Image.Image)

    def test_end(self, robot_face_app, mock_output):
        """end メソッドのテスト."""
        robot_face_app.end()
        mock_output.close.assert_called_once()

    @patch("time.sleep")
    def test_handle_random_mood_update(self, mock_sleep, robot_face_app):
        """ランダムモードでの表情更新テスト (間接的に)"""
        with pytest.raises(
            AttributeError
        ):  # または、メソッドがもはや存在しないことを検証する
            robot_face_app._handle_random_mood_update(time.time())

    @patch("time.sleep")
    def test_handle_gaze_update(self, mock_sleep, robot_face_app):
        """ランダムモードでの視線更新テスト (間接的に)"""
        # _handle_gaze_update も RandomMode の内部に移ったため
        # ここでは RobotFaceApp の direct なテストは不要
        with pytest.raises(
            AttributeError
        ):  # または、メソッドがもはや存在しないことを検証する
            robot_face_app._handle_gaze_update(time.time())


class TestMainCLI:
    """CLI の main 関数のテスト"""

    @patch("samples.robot_face_animation3.create_output_device")
    def test_help(self, mock_create_output):
        """--help オプションのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        runner = CliRunner()
        result = runner.invoke(robot_face_animation3_main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    @patch("samples.robot_face_animation3.create_output_device")
    @patch("time.sleep")
    def test_random_mode(self, mock_sleep, mock_create_output):
        """ランダムモードのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        # time.sleep で KeyboardInterrupt を発生させてループを止める
        mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

        runner = CliRunner()
        result = runner.invoke(robot_face_animation3_main, ["--random"])
        assert result.exit_code == 0
        mock_sleep.assert_called()
        mock_output.show.assert_called()  # render_frame が呼ばれたことを確認

    @patch("samples.robot_face_animation3.create_output_device")
    @patch("time.sleep")
    def test_sequence_mode(self, mock_sleep, mock_create_output):
        """シーケンスモードのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        # time.sleep で KeyboardInterrupt を発生させてループを止める
        mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

        runner = CliRunner()
        result = runner.invoke(robot_face_animation3_main, ["_O_O", "/O_O"])
        assert result.exit_code == 0
        mock_sleep.assert_called()
        mock_output.show.assert_called()  # render_frame が呼ばれたことを確認

    @patch("samples.robot_face_animation3.create_output_device")
    @patch(
        "builtins.input", side_effect=["_OO_", "q"]
    )  # ユーザー入力のモック
    @patch("time.sleep")
    def test_interactive_mode(
        self, mock_sleep, mock_input, mock_create_output
    ):
        """インタラクティブモードのテスト."""
        mock_output = MagicMock()
        mock_create_output.return_value = mock_output

        mock_sleep.side_effect = KeyboardInterrupt(
            "Stop loop"
        )  # ループを抜けるため

        runner = CliRunner()
        result = runner.invoke(
            robot_face_animation3_main, []
        )  # 引数なしでインタラクティブモード
        assert result.exit_code == 0
        mock_input.assert_any_call("顔の記号 (例: _OO_, qで終了): ")
        mock_output.show.assert_called()  # render_frame が呼ばれたことを確認
