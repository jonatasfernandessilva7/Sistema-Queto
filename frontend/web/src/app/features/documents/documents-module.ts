import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { DocumentsRoutingModule } from './documents-routing-module';
import { DocumentsComponent } from './pages/documents/documents';
@NgModule({ imports: [SharedModule, DocumentsRoutingModule, DocumentsComponent] })
export class DocumentsModule {}
