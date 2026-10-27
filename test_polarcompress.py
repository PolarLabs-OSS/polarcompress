import tempfile
from pathlib import Path
from PIL import Image
from polarcompress import convert_image,unique_output
with tempfile.TemporaryDirectory() as d:
 p=Path(d); original=p/'original.png'; Image.new('RGBA',(200,100),(120,50,60,100)).save(original)
 targets=set(); target=unique_output(p,'result','.jpg',targets)
 a,b=convert_image(original,target,'JPEG',80,100,100)
 with Image.open(target) as im:
  assert im.size==(100,50) and im.mode=='RGB'
 assert a>0 and b>0 and original.exists()
 assert unique_output(p,'result','.jpg',targets).name=='result_2.jpg'
 output=p/'result.webp'; convert_image(original,output,'WEBP',80)
 with Image.open(output) as im:assert im.size==(200,100)
 try:convert_image(original,original,'PNG');raise AssertionError('overwrite must fail')
 except ValueError:pass
 print('PASS: JPEG, WebP, resize, alpha handling, collision, overwrite protection')
