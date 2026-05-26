import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './core/services/theme';
import { ToastService } from './core/services/toast';
import { SharedModule } from './shared/shared-module';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, SharedModule],
  templateUrl: './app.component.html',
})
export class AppComponent implements OnInit {
  constructor(
    readonly theme: ThemeService,
    readonly toast: ToastService,
  ) {}
  ngOnInit(): void { this.theme.apply(); }
}
