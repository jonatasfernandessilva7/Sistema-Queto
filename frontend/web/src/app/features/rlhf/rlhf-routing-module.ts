import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { RlhfComponent } from './pages/rlhf/rlhf';
const routes: Routes = [{ path: '', component: RlhfComponent }];
@NgModule({ imports: [RouterModule.forChild(routes)], exports: [RouterModule] })
export class RlhfRoutingModule {}
