import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface NavItem { label: string; icon: string; route: string; }

@Component({ selector: 'app-sidebar', templateUrl: './sidebar.html', styleUrls: ['./sidebar.scss'], standalone: true, imports: [CommonModule, RouterModule] })
export class SidebarComponent {
  readonly nav: NavItem[] = [
    { label: 'Dashboard',   icon: '⬡', route: '/dashboard' },
    { label: 'Áudio',       icon: '🎙', route: '/audio' },
    { label: 'Documentos',  icon: '📄', route: '/documents' },
    { label: 'Relatórios',  icon: '📊', route: '/reports' },
    { label: 'Eventos',     icon: '⚡', route: '/events' },
    { label: 'Feedback',        icon: '🧠', route: '/rlhf' },
  ];
}
