import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { ReportsRoutingModule } from './reports-routing-module';
import { ReportsComponent } from './pages/reports/reports';
@NgModule({ imports: [SharedModule, ReportsRoutingModule, ReportsComponent] })
export class ReportsModule {}
