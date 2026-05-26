import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

@Pipe({ name: 'safeUrl', standalone: true })
export class SafeUrlPipe implements PipeTransform {
  constructor(private san: DomSanitizer) {}
  transform(url: string): SafeResourceUrl {
    return this.san.bypassSecurityTrustResourceUrl(url);
  }
}
