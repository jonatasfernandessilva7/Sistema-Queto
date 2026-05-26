import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { AudioRoutingModule } from './audio-routing-module';
import { AudioUploadComponent } from './pages/audio-upload/audio-upload';
@NgModule({ imports: [SharedModule, AudioRoutingModule, AudioUploadComponent] })
export class AudioModule {}
