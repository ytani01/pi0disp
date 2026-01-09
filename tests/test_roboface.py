import pytest
from PIL import Image

from samples.roboface import (
    RfConfig,
    RfParser,
    RfState,
    RobotFace,
)


class TestRfStructure:
    def test_config_constants(self):
        """定数が正しく定義されているか"""
        assert RfConfig.SIZE == 240
        assert "face_bg" in RfConfig.COLORS

    def test_state_immutability(self):
        """RfStateのデフォルト値が独立しているか"""
        state1 = RfState()
        state2 = RfState()
        assert state1 is not state2
        assert state1.left_eye is not state2.left_eye

    def test_parser(self):
        """文字列パースの動作確認"""
        parser = RfParser()
        # 正常系 (エイリアス)
        state = parser.parse("neutral")
        assert isinstance(state, RfState)
        assert state.left_eye.open == 1.0

        # 正常系 (4文字直接)
        state4 = parser.parse("_OO_")
        assert isinstance(state4, RfState)

        # 異常系 (4文字以外)
        with pytest.raises(ValueError):
            parser.parse("too_long_string")

    # def test_renderer(self):
    #     """レンダラーが画像を生成できるか"""
    #     renderer = RfRenderer(size=RfConfig.SIZE)
    #     state = RfState()
    #
    #     # アウトライン描画
    #     img_outline = renderer.render_outline(320, 240, (0, 0, 0))
    #     assert isinstance(img_outline, Image.Image)
    #     assert img_outline.size == (320, 240)
    #
    #     # パーツ描画
    #     img_parts = renderer.render_parts(state, 0.0, 320, 240, (0, 0, 0))
    #     assert isinstance(img_parts, Image.Image)
    #     assert img_parts.size == (320, 240)

    def test_robot_face_interface(self):
        """RobotFaceの公開インターフェース確認"""
        face = RobotFace(RfState())

        # 状態更新
        face.set_gaze(0.5)
        face.update()
        assert face.is_changing is False

        # 描画イメージ取得
        img = face.get_parts_image(320, 240, (0, 0, 0))
        assert isinstance(img, Image.Image)

        # 表情変更
        new_state = face.parser.parse("happy")
        face.start_change(new_state)
        assert face.is_changing is True

        # アニメーション中の描画
        img2 = face.get_parts_image(320, 240, (0, 0, 0))
        assert isinstance(img2, Image.Image)

        # キューへの投入
        face.enqueue_face("sad")

    def test_robot_face_state_update(self):
        """RobotFace.update() が内部状態を実際に遷移させているか検証する。"""
        import time

        parser = RfParser()
        initial_face = parser.parse("_OO_")
        robot = RobotFace(initial_face, size=240)

        target_face = parser.parse("vOOv")  # 眉を v (25.0) に変更
        robot.start_change(target_face, duration=0.1)
        assert robot.is_changing is True

        time.sleep(0.05)
        robot.update()
        mid_tilt = robot.updater.current_face.brow.tilt
        assert mid_tilt != initial_face.brow.tilt

        time.sleep(0.1)
        robot.update()
        final_tilt = robot.updater.current_face.brow.tilt

        assert robot.is_changing is False
        assert final_tilt == target_face.brow.tilt
