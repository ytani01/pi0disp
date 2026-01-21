#
# (c) 2026 Yoichi Tanibayashi
#
import os
import tomlkit
from pi0disp.utils.my_conf import update_toml_settings

def test_update_toml_settings(tmp_path):
    conf_file = tmp_path / "pi0disp.toml"
    
    # 1. 新規作成
    update_toml_settings({"bgr": True, "invert": False}, str(conf_file))
    
    with open(conf_file, "r") as f:
        data = tomlkit.parse(f.read())
    
    assert data["pi0disp"]["bgr"] is True
    assert data["pi0disp"]["invert"] is False
    
    # 2. 既存ファイルの更新 (コメントを維持するか)
    content = """
[pi0disp]
# This is a comment
bgr = false
invert = true
"""
    with open(conf_file, "w") as f:
        f.write(content)
        
    update_toml_settings({"bgr": True}, str(conf_file))
    
    with open(conf_file, "r") as f:
        new_content = f.read()
        
    assert "bgr = true" in new_content
    assert "invert = true" in new_content # 維持されていること
    assert "# This is a comment" in new_content # コメントが維持されていること
