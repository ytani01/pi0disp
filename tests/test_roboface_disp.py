from unittest.mock import MagicMock
from PIL import Image
from samples.roboface import CV2Disp, RobotFace, RfState

def test_cv2_disp_display_signature():
    """
    Test that CV2Disp.display now accepts 'full' argument.
    """
    disp = CV2Disp(width=320, height=240)
    disp._show = MagicMock()  # type: ignore[method-assign]
    img = Image.new("RGB", (320, 240))
    
    # This should NOT fail now
    disp.display(img, full=True)
    
    disp._show.assert_called_once_with(img)

def test_robot_face_draw_with_cv2_no_crash():
    """
    Test that RobotFace.draw does not crash when using CV2Disp.
    """
    state = RfState()
    rf = RobotFace(face=state, size=240)
    
    disp = CV2Disp(width=320, height=240)
    disp._show = MagicMock()  # type: ignore[method-assign]
    
    # RobotFace.draw calls disp.display(img, full=full)
    # This should NOT fail now
    rf.draw(disp, bg_color="black", full=True)
    
    assert disp._show.called
