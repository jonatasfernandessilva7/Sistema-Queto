import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api';
import { AudioProcessResult } from '../models';

@Injectable({ providedIn: 'root' })
export class AudioService {
  constructor(private api: ApiService) {}

  uploadAudio(file: File): Observable<AudioProcessResult> {
    const form = new FormData();
    form.append('audio_file', file, file.name);
    return this.api.postForm<AudioProcessResult>('/v1/u/process-audio', form);
  }

  startRecording(): Observable<unknown> { return this.api.post('/v1/u/start-recording'); }
  stopRecording(): Observable<AudioProcessResult> { return this.api.post('/v1/u/stop-recording'); }
}
