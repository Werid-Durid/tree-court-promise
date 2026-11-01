"""Stream Eevee-rendered PNG frames to FFmpeg without keeping frame directories."""
import bpy,subprocess,time
from pathlib import Path
FFMPEG=Path('C:/Users/洛薇/.video-watch/tools/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe')
def render_video(scene,target,duration,sound=None):
 target=Path(target);partial=target.with_name(target.stem+'.rendering.mp4');frame=target.with_name('_'+target.stem+'-render-frame.png')
 args=[str(FFMPEG),'-hide_banner','-loglevel','error','-y','-framerate','24','-f','image2pipe','-vcodec','png','-i','pipe:0']
 if sound:args+=['-i',str(sound),'-map','0:v:0','-map','1:a:0','-af','apad','-c:a','aac','-b:a','192k']
 args+=['-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-t',str(duration),'-movflags','+faststart',str(partial)]
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.compression=5;scene.render.filepath=str(frame)
 started=time.monotonic()
 with (target.parent/(target.stem+'-encode.log')).open('w',encoding='utf-8') as errors:
  process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=errors)
  try:
   for index in range(round(duration*24)):
    scene.frame_set(index+1);bpy.ops.render.render(write_still=True);process.stdin.write(frame.read_bytes())
    if index%24==0:print('RENDER_PROGRESS',target.name,index+1,round(duration*24),round(time.monotonic()-started,1),flush=True)
   process.stdin.close();code=process.wait()
   if code:raise RuntimeError(f'FFmpeg failed: {target.name}, code {code}')
  except BaseException:
   process.kill();process.wait();raise
  finally:frame.unlink(missing_ok=True)
 partial.replace(target)
