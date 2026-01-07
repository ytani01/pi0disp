import pytest
from PIL import Image
from samples.roboface2 import RfConfig, RfState, RfParser, RfRenderer, RobotFace

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
        
    def test_renderer(self):
        """レンダラーが画像を生成できるか"""
        renderer = RfRenderer(size=RfConfig.SIZE)
        state = RfState()
        
        # アウトライン描画
        img_outline = renderer.render_outline(320, 240, (0, 0, 0))
        assert isinstance(img_outline, Image.Image)
        assert img_outline.size == (320, 240)
        
        # パーツ描画
        img_parts = renderer.render_parts(state, 0.0, 320, 240, (0, 0, 0))
        assert isinstance(img_parts, Image.Image)
        assert img_parts.size == (320, 240)

    def test_robot_face_interface(self):
        """RobotFaceの公開インターフェース確認"""
        face = RobotFace(RfState())
        
        # 画像取得
        img_outline = face.get_outline_image(320, 240, (0, 0, 0))
        assert isinstance(img_outline, Image.Image)
        
        img_parts = face.get_parts_image(320, 240, (0, 0, 0))
        assert isinstance(img_parts, Image.Image)
        
        # 状態更新
        face.set_gaze(0.5)
        face.update()
        # エラーが出なければOK