import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { DashboardRoutingModule } from './dashboard-routing-module';
import { DashboardComponent } from './pages/dashboard/dashboard';
@NgModule({ imports: [SharedModule, DashboardRoutingModule, DashboardComponent] })
export class DashboardModule {}
