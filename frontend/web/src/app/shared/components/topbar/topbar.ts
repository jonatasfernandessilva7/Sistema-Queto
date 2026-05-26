import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThemeService } from '../../../core/services/theme';

@Component({ selector: 'app-topbar', templateUrl: './topbar.html', styleUrls: ['./topbar.scss'], standalone: true, imports: [CommonModule] })
export class TopbarComponent {
  constructor(readonly theme: ThemeService) {}
}
