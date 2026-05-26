import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { EventsRoutingModule } from './events-routing-module';
import { EventsComponent } from './pages/events/events';
@NgModule({ imports: [SharedModule, EventsRoutingModule, EventsComponent] })
export class EventsModule {}
