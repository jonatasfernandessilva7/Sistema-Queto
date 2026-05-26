import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', loadChildren: () => import('./features/dashboard/dashboard-module').then(m => m.DashboardModule) },
  { path: 'audio',     loadChildren: () => import('./features/audio/audio-module').then(m => m.AudioModule) },
  { path: 'documents', loadChildren: () => import('./features/documents/documents-module').then(m => m.DocumentsModule) },
  { path: 'reports',   loadChildren: () => import('./features/reports/reports-module').then(m => m.ReportsModule) },
  { path: 'events',    loadChildren: () => import('./features/events/events-module').then(m => m.EventsModule) },
  { path: 'rlhf',      loadChildren: () => import('./features/rlhf/rlhf-module').then(m => m.RlhfModule) },
  { path: '**', redirectTo: 'dashboard' },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule {}
