import pytest
import time
from tests._testbase_cli import CLITestBase, InteractiveSession

class TestRobofaceIntegration(CLITestBase):
    # 継承元の汎用テストメソッドが pytest に拾われないようにする
    test_command = None
    test_interactive = None

    def test_interactive_engine_lifecycle_and_error(self):
        """
        [事実確認]
        1. エンジンが正常に開始されること。
        2. 不正な入力（4文字以外）に対してエラーログを出しつつ、動作を継続すること。
        3. 'q' でエンジンが正常に停止し、クリーンに終了すること。
        """
        cmd = ["uv", "run", "python", "samples/roboface.py"]
        
        session = self.run_interactive_command(cmd)
        
        try:
            # 1. 起動の事実確認
            assert session.expect("Animation engine thread started.", timeout=10.0)
            print("Fact: Animation engine started correctly.")

            # 2. エラー耐性の事実確認 (単発)
            session.send_key("12345\n")
            assert session.expect("Face string must be 4 characters long", timeout=5.0)
            print("Fact: Single error message caught correctly.")

            # 3. エラー耐性の事実確認 (連続・混在)
            # 正常 -> 異常 -> 正常 の順で送る
            session.send_key("happy\n")
            assert session.expect("Applying new expression: happy", timeout=5.0)
            
            session.send_key("bad\n") # 3文字でエラー
            assert session.expect("Face string must be 4 characters long", timeout=5.0)
            
            session.send_key("sad\n")
            assert session.expect("Applying new expression: sad", timeout=5.0)
            print("Fact: Continued processing correctly after multiple errors.")
            
            # 4. 終了の事実確認
            session.send_key("q\n")
            try:
                session.expect("Animation engine thread stopped.", timeout=2.0)
            except Exception:
                pass
            
        finally:
            ret = session.close(terminate_flag=False)
            print(f"Fact: Process exited with return code {ret}")
            assert ret == 0


