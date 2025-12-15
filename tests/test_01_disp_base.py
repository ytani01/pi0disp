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

        self.patcher_pigpio = mock.patch("pi0disp.disp.disp_base.pigpio")
        self.patcher_logger = mock.patch("pi0disp.disp.disp_base.get_logger")

        self.mock_pigpio = self.patcher_pigpio.start()
        self.mock_logger_getter = self.patcher_logger.start()

        self.addCleanup(self.patcher_pigpio.stop)
        self.addCleanup(self.patcher_logger.stop)

        self.mock_pi_instance = self._setup_pi_mock()

    def _setup_pi_mock(self, connected=True):
        """pigpioモックをセットアップするヘルパー"""
        mock_pi_instance = mock.Mock()
        mock_pi_instance.connected = connected
        self.mock_pigpio.pi.return_value = mock_pi_instance
        return mock_pi_instance

    def _create_disp_base_instance(
        self, size=None, rotation=None, debug=False
    ):
        """
        テスト用のDispBaseインスタンスを生成するヘルパーメソッド。
        必要に応じてデフォルト値を使用し、setUpで設定されたモックを使用する。
        """
        if size is None:
            size = self.default_size
        if rotation is None:
            raise ValueError("rotation must be specified")
        return DispBase(size, rotation, debug)

    def test_init_success(self):
        """インスタンス化が成功するケースのテスト"""
        disp_base = self._create_disp_base_instance(
            size=self.default_size,
            rotation=self.default_rotation,
            debug=False,
        )

        self.mock_pigpio.pi.assert_called_once()
        self.mock_logger_getter.assert_called_once_with("DispBase", False)
        self.assertTrue(disp_base.pi.connected)

        # DispBase.__init__でrotationが考慮され、sizeがスワップされる
        self.assertEqual(disp_base.size["width"], self.default_size["height"])
        self.assertEqual(disp_base.size["height"], self.default_size["width"])

        self.assertEqual(disp_base._native_size, self.default_size)
        self.assertEqual(disp_base._rotation, self.default_rotation)

    def test_init_pigpio_connection_error(self):
        """pigpioへの接続失敗時にRuntimeErrorを送出するテスト"""
        self._setup_pi_mock(connected=False)

        with self.assertRaises(RuntimeError) as cm:
            self._create_disp_base_instance(
                size=self.default_size, rotation=self.default_rotation
            )
        self.assertIn("Could not connect to pigpio daemon", str(cm.exception))
        self.mock_pigpio.pi.assert_called_once()

    def test_init_display(self):
        """init_displayが警告ログを出すことをテスト"""
        mock_logger = mock.Mock()
        self.mock_logger_getter.return_value = mock_logger

        disp_base = self._create_disp_base_instance(rotation=0)
        disp_base.init_display()

        mock_logger.warning.assert_called_once_with(
            "Please override this method."
        )

    def test_set_rotation_to_90(self):
        """set_rotationで90度回転したときのsizeの変更をテスト"""
        disp_base = self._create_disp_base_instance(rotation=0)
        disp_base.set_rotation(90)
        self.assertEqual(disp_base.size["width"], self.default_size["height"])
        self.assertEqual(disp_base.size["height"], self.default_size["width"])
        self.assertEqual(disp_base._rotation, 90)

    def test_set_rotation_to_0(self):
        """set_rotationで0度回転（元に戻す）したときのsizeの変更をテスト"""
        # 初期状態を90度回転にしてから0度に戻すシナリオをテスト
        initial_rotation = 90
        disp_base = self._create_disp_base_instance(rotation=initial_rotation)
        # 90度回転しているので、widthとheightがスワップされている状態を想定
        self.assertEqual(disp_base.size["width"], self.default_size["height"])
        self.assertEqual(disp_base.size["height"], self.default_size["width"])

        disp_base.set_rotation(0)
        self.assertEqual(disp_base.size["width"], self.default_size["width"])
        self.assertEqual(
            disp_base.size["height"], self.default_size["height"]
        )
        self.assertEqual(disp_base._rotation, 0)

    def test_display_resizes_image(self):
        """displayが画像をリサイズするかをテスト"""
        disp_base = self._create_disp_base_instance(
            rotation=self.default_rotation
        )

        mock_image = mock.Mock(spec=Image.Image)
        mock_image.size = (100, 100)

        disp_base.display(mock_image)

        expected_size = (disp_base.size["width"], disp_base.size["height"])
        mock_image.resize.assert_called_once_with(expected_size)

    def test_display_with_correct_size_image(self):
        """displayが画像のリサイズをしないことをテスト（サイズが既に正しい場合）"""
        disp_base = self._create_disp_base_instance(
            rotation=self.default_rotation
        )

        mock_image = mock.Mock(spec=Image.Image)
        mock_image.size = (disp_base.size["width"], disp_base.size["height"])

        disp_base.display(mock_image)

        mock_image.resize.assert_not_called()

    def test_close_calls_pi_stop_when_connected(self):
        """connected=Trueの場合にcloseがpi.stop()を呼び出すかをテスト"""
        # mock_pi_instanceはsetUpでself.mock_pi_instanceとして設定済み
        disp_base = self._create_disp_base_instance(rotation=0)

        disp_base.close()
        self.mock_pi_instance.stop.assert_called_once()

    def test_close_does_not_call_pi_stop_when_not_connected(self):
        """connected=Falseの場合にcloseがpi.stop()を呼び出さないかをテスト"""
        # DispBaseが正常にインスタンス化されるように、pi.connectedはTrueにする
        # mock_pi_instanceはsetUpでself.mock_pi_instanceとして設定済み
        disp_base = self._create_disp_base_instance(rotation=0)

        # テストしたい条件（connected=False）をインスタンス化後に設定
        disp_base.pi.connected = False

        disp_base.close()
        self.mock_pi_instance.stop.assert_not_called()


# テストを直接実行するための標準的な記述
if __name__ == "__main__":
    unittest.main()
