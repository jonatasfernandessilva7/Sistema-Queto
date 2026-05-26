import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/pages/dashboard/dashboard').then(m => m.DashboardComponent),
  },
  {
    path: 'audio',
    loadComponent: () =>
      import('./features/audio/pages/audio-upload/audio-upload').then(m => m.AudioUploadComponent),
  },
  {
    path: 'documents',
    loadComponent: () =>
      import('./features/documents/pages/documents/documents').then(m => m.DocumentsComponent),
  },
  {
    path: 'reports',
    loadComponent: () =>
      import('./features/reports/pages/reports/reports').then(m => m.ReportsComponent),
  },
  {
    path: 'events',
    loadComponent: () =>
      import('./features/events/pages/events/events').then(m => m.EventsComponent),
  },
  {
    path: 'rlhf',
    loadComponent: () =>
      import('./features/rlhf/pages/rlhf/rlhf').then(m => m.RlhfComponent),
  },
  { path: '**', redirectTo: 'dashboard' },
];
