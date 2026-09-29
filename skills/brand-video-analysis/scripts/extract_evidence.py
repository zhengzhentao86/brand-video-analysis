#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract verifiable media artifacts. Does not perform visual analysis."""
import argparse, hashlib, json, math, re, shutil, subprocess, sys
from pathlib import Path


def run(argv):
    try:
        return subprocess.run(argv, check=True, capture_output=True, text=True, timeout=180).stdout
    except subprocess.CalledProcessError as exc:
        # Arguments never contain remote media URLs. Keep output bounded.
        raise RuntimeError(f'{Path(argv[0]).name} failed: {exc.stderr[-600:]}') from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f'{Path(argv[0]).name} timed out') from exc


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--video',required=True,type=Path);p.add_argument('--id',required=True)
    p.add_argument('--out',required=True,type=Path);p.add_argument('--scan-step',type=float,default=5)
    p.add_argument('--key-times',default='');p.add_argument('--asr-model');p.add_argument('--language')
    a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',a.id):p.error('id must use letters, digits, _ or -')
    if not math.isfinite(a.scan_step) or a.scan_step<=0:p.error('scan-step must be positive and finite')
    for cmd in ['ffmpeg','ffprobe']:
        if not shutil.which(cmd):p.error(f'{cmd} unavailable')
    source=a.video.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(source.read_bytes()).hexdigest();mp=out/'manifest.json'
    previous=json.loads(mp.read_text()) if mp.exists() else {}
    if previous and (previous.get('sha256')!=digest or previous.get('asset_id')!=a.id):
        p.error('Output belongs to a different video/id; choose a new folder')
    probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(source)]))
    duration=float(probe['format']['duration'])
    if not math.isfinite(duration) or duration<=0:p.error('Invalid duration')
    streams=probe.get('streams',[])
    if not any(s.get('codec_type')=='video' for s in streams):p.error('No video stream')
    video_stream=next(s for s in streams if s.get('codec_type')=='video')
    video_duration=float(video_stream.get('duration') or duration)
    if not math.isfinite(video_duration) or video_duration<=0:video_duration=duration
    sample_end=min(duration,video_duration)
    times={float(i) for i in range(6) if i<sample_end}
    times.add(max(0,round(sample_end-.1,3)))
    t=6.
    while t<sample_end:
        times.add(round(t,3));t+=a.scan_step
    keys=[float(x) for x in a.key_times.split(',') if x.strip()]
    if any(not math.isfinite(t) or not 0<=t<sample_end for t in keys):p.error('Key time outside actual video duration')
    times.update(keys);times.update(f['time'] for f in previous.get('frames',[]) if f['time']<sample_end)
    rows=[];warnings=[]
    for t in sorted(times):
        name=f'frame-{t:010.3f}'.replace('.','p')+'.jpg';f=out/name
        if not f.exists():
            run(['ffmpeg','-nostdin','-y','-v','error','-ss',str(t),'-i',str(source),'-frames:v','1','-q:v','3',str(f)])
        if not f.exists() or not f.stat().st_size:
            warnings.append(f'No decoded frame at {t:.3f}s');continue
        rows.append({'time':t,'file':name,'review_status':'待目视核验'})
    has_audio=any(s.get('codec_type')=='audio' for s in streams)
    wav=out/'audio.wav'
    if has_audio and not wav.exists():
        run(['ffmpeg','-nostdin','-y','-v','error','-i',str(source),'-vn','-ar','16000','-ac','1',str(wav)])
    audio_status=(previous.get('audio_status','已提取待核验') if (out/'asr.json').exists() else '已提取待核验') if has_audio else '源文件无音频流'
    asr_result=None
    if a.asr_model and has_audio:
        try:
            from faster_whisper import WhisperModel
            model=WhisperModel(a.asr_model,device='cpu',compute_type='int8',local_files_only=True)
            segments,_=model.transcribe(str(wav),language=a.language,beam_size=5,vad_filter=True,condition_on_previous_text=False)
            asr_result=[{'start':s.start,'end':s.end,'text':s.text,'no_speech_prob':s.no_speech_prob} for s in segments]
            (out/'asr.json').write_text(json.dumps(asr_result,ensure_ascii=False,indent=2))
            audio_status='音轨已自动转写，待校对' if asr_result else 'ASR未检出可辨识语音，不代表绝对无口播'
        except Exception as exc:
            warnings.append('ASR unavailable: '+type(exc).__name__);audio_status='音轨已提取，转写失败，未核验'
    sheets=[]
    try:
        from PIL import Image,ImageDraw
        for start in range(0,len(rows),24):
            batch=rows[start:start+24];sheet=Image.new('RGB',(1080,346*math.ceil(len(batch)/6)),'#f4f1e9');draw=ImageDraw.Draw(sheet)
            for j,item in enumerate(batch):
                with Image.open(out/item['file']) as im:
                    im=im.convert('RGB');im.thumbnail((180,320));x=j%6*180;y=j//6*346
                    sheet.paste(im,(x+(180-im.width)//2,y));draw.text((x+4,y+322),f'{a.id} / {item["time"]:.3f}s',fill='#232a24')
            name=f'contact-{start//24+1:02}.jpg';sheet.save(out/name,quality=90);sheets.append(name)
    except ImportError:warnings.append('Pillow unavailable; inspect individual frames')
    result={'asset_id':a.id,'sha256':digest,'bytes':source.stat().st_size,'duration':duration,'video_duration':video_duration,'media_status':'已解码抽帧，未完成目视分析','audio_status':audio_status,'audio_file':'audio.wav' if has_audio else None,'frames':rows,'contact_sheets':sheets,'warnings':warnings}
    mp.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'asset_id':a.id,'duration':duration,'frames':len(rows),'audio_status':audio_status,'warnings':warnings},ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,ValueError,KeyError) as exc:
        print(f'Error: {exc}',file=sys.stderr);sys.exit(1)
