from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mocker_pigpio():
    """
    pigpio.pi()をモックするためのフィクスチャ。

    実際のpigpioライブラリの代わりに、MagicMockオブジェクトを返す。
    これにより、ハードウェア(Raspberry Pi)がない環境でも、
    pigpioに依存するコードの単体テストが可能になる。

    モックは、呼び出されたメソッドやその引数を記録するため、
    テストコードで意図した通りにメソッドが呼ばれたかを確認できる。

    使用例:
    def test_some_function(mocker_pigpio):
        # mocker_pigpioを使ってテスト対象のオブジェクトを初期化
        pi = mocker_pigpio()
        servo = PiServo(pi, 17)

        # メソッドを実行
        servo.move_center()

        # 意図した通りにメソッドが呼ばれたかを確認
        pi.set_servo_pulsewidth.assert_called_with(17, 1500)
    """
    # 'pigpio.pi'をMagicMockで置き換える
    with patch("pigpio.pi") as mock_pi_constructor:
        # pi()コンストラクタが返すインスタンスのモックを作成
        mock_pi_instance = MagicMock()

        # get_servo_pulsewidthのデフォルトの戻り値を設定
        # 具体的なテストケースで上書き可能
        mock_pi_instance.reset_mock()  # 初期化時のoff()呼び出しをクリア

        # pi()が呼ばれたら、上記で作成したインスタンスのモックを返すように設定
        mock_pi_constructor.return_value = mock_pi_instance

        # このフィクスチャを使用するテストに、
        # pi()コンストラクタのモックを渡す
        yield mock_pi_constructor
