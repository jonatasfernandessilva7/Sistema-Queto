import { NgModule } from '@angular/core';
import { SharedModule } from '../../shared/shared-module';
import { RlhfRoutingModule } from './rlhf-routing-module';
import { RlhfComponent } from './pages/rlhf/rlhf';
@NgModule({ imports: [SharedModule, RlhfRoutingModule, RlhfComponent] })
export class RlhfModule {}
