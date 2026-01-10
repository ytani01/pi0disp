import pytest
from unittest.mock import MagicMock
from PIL import Image
from samples.roboface import CV2Disp, RobotFace, RfState

def test_cv2_disp_display_signature():
    """
    Test that CV2Disp.display fails when called with 'full' argument
    (current buggy state).
    """
    disp = CV2Disp(width=320, height=240)
    img = Image.new("RGB", (320, 240))
    
    # This should fail with TypeError: display() got an unexpected keyword argument 'full'
    with pytest.raises(TypeError) as excinfo:
        disp.display(img, full=True)
    
    assert "unexpected keyword argument 'full'" in str(excinfo.value)

def test_robot_face_draw_with_cv2_crash():
    """
    Test that RobotFace.draw causes a crash when using CV2Disp.
    """
    state = RfState()
    rf = RobotFace(face=state, size=240)
    
    # Mock CV2Disp to avoid actual window creation but keep signature
    # Actually, we want to test the real CV2Disp class behavior if possible, 
    # but cv2 might not be available or might fail in headless CI.
    # So we use the real class but mock the internal _show method.
    disp = CV2Disp(width=320, height=240)
    disp._show = MagicMock()
    
    img = Image.new("RGB", (320, 240))
    
    # RobotFace.draw calls disp.display(img, full=full)
    with pytest.raises(TypeError) as excinfo:
        rf.draw(disp, bg_color="black", full=True)
        
    assert "unexpected keyword argument 'full'" in str(excinfo.value)
