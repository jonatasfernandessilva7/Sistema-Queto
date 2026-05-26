import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AudioUploadComponent } from './pages/audio-upload/audio-upload';
const routes: Routes = [{ path: '', component: AudioUploadComponent }];
@NgModule({ imports: [RouterModule.forChild(routes)], exports: [RouterModule] })
export class AudioRoutingModule {}
