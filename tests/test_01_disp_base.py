# tests/test_01_disp_base.py

import unittest
from unittest import mock

from PIL import Image

from pi0disp.disp.disp_base import DispBase


class TestDispBase(unittest.TestCase):
    def setUp(self):
        """各テストの前に実行されるセットアップ"""
        self.default_size = {"width": 240, "height": 320}
        self.default_rotation = 270

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_init_success(self, mock_pigpio, mock_get_logger):
        """インスタンス化が成功するケースのテスト"""
        mock_pi_instance = mock.Mock()
        mock_pi_instance.connected = True
        mock_pigpio.pi.return_value = mock_pi_instance

        disp_base = DispBase(
            size=self.default_size,
            rotation=self.default_rotation,
            debug=False,
        )

        mock_pigpio.pi.assert_called_once()
        mock_get_logger.assert_called_once_with("DispBase", False)
        self.assertTrue(disp_base.pi.connected)

        # DispBase.__init__はrotationを考慮しないので、sizeはそのままのはず
        self.assertEqual(disp_base.size["width"], self.default_size["width"])
        self.assertEqual(
            disp_base.size["height"], self.default_size["height"]
        )

        self.assertEqual(disp_base._native_size, self.default_size)
        self.assertEqual(disp_base._rotation, self.default_rotation)

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_init_pigpio_connection_error(self, mock_pigpio, mock_get_logger):
        """pigpioへの接続失敗時にRuntimeErrorを送出するテスト"""
        mock_pi_instance = mock.Mock()
        mock_pi_instance.connected = False
        mock_pigpio.pi.return_value = mock_pi_instance

        with self.assertRaises(RuntimeError) as cm:
            DispBase(size=self.default_size, rotation=self.default_rotation)
        self.assertIn("Could not connect to pigpio daemon", str(cm.exception))
        mock_pigpio.pi.assert_called_once()

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_init_display(self, mock_pigpio, mock_get_logger):
        """init_displayが警告ログを出すことをテスト"""
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger

        disp_base = DispBase(self.default_size, 0)
        disp_base.init_display()

        mock_logger.warning.assert_called_once_with(
            "Please override this method."
        )

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_set_rotation(self, mock_pigpio, mock_get_logger):
        """set_rotationによるsizeの変更をテスト"""
        disp_base = DispBase(self.default_size, 0)

        # 90度回転
        disp_base.set_rotation(90)
        self.assertEqual(disp_base.size["width"], self.default_size["height"])
        self.assertEqual(disp_base.size["height"], self.default_size["width"])
        self.assertEqual(disp_base._rotation, 90)

        # 0度回転 (元に戻す)
        disp_base.set_rotation(0)
        self.assertEqual(disp_base.size["width"], self.default_size["width"])
        self.assertEqual(
            disp_base.size["height"], self.default_size["height"]
        )
        self.assertEqual(disp_base._rotation, 0)

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_display(self, mock_pigpio, mock_get_logger):
        """displayが画像をリサイズするかをテスト"""
        disp_base = DispBase(self.default_size, 0)
        # set_rotationを呼ばないとsizeがスワップされないので呼ぶ
        disp_base.set_rotation(self.default_rotation)

        mock_image = mock.Mock(spec=Image.Image)
        mock_image.size = (100, 100)

        disp_base.display(mock_image)

        expected_size = (disp_base.size["width"], disp_base.size["height"])
        mock_image.resize.assert_called_once_with(expected_size)

    @mock.patch("pi0disp.disp.disp_base.get_logger")
    @mock.patch("pi0disp.disp.disp_base.pigpio")
    def test_close(self, mock_pigpio, mock_get_logger):
        """closeがpi.stop()を呼び出すかをテスト"""
        mock_pi_instance = mock.Mock()
        mock_pi_instance.connected = True
        mock_pigpio.pi.return_value = mock_pi_instance

        disp_base = DispBase(self.default_size, 0)

        # connected = Trueの場合
        disp_base.close()
        mock_pi_instance.stop.assert_called_once()

        # connected = Falseの場合
        mock_pi_instance.reset_mock()
        disp_base.pi.connected = False
        disp_base.close()
        mock_pi_instance.stop.assert_not_called()


# テストを直接実行するための標準的な記述
if __name__ == "__main__":
    unittest.main()
