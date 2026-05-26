import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { SidebarComponent }     from './components/sidebar/sidebar';
import { TopbarComponent }      from './components/topbar/topbar';
import { CrisisBadgeComponent } from './components/crisis-badge/crisis-badge';
import { GaugeChartComponent }  from './components/gauge-chart/gauge-chart';
import { BarChartComponent }    from './components/bar-chart/bar-chart';
import { RadarChartComponent }  from './components/radar-chart/radar-chart';
import { SparklineComponent }   from './components/sparkline/sparkline';
import { SafeUrlPipe }          from './pipes/safe-url.pipe';

@NgModule({
  imports: [CommonModule, RouterModule, FormsModule, ReactiveFormsModule, SidebarComponent, TopbarComponent, CrisisBadgeComponent, GaugeChartComponent, BarChartComponent, RadarChartComponent, SparklineComponent, SafeUrlPipe],
  exports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    SidebarComponent, TopbarComponent, CrisisBadgeComponent,
    GaugeChartComponent, BarChartComponent, RadarChartComponent,
    SparklineComponent, SafeUrlPipe,
  ],
})
export class SharedModule {}
