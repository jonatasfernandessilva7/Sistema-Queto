import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CrisisBadge } from './crisis-badge';

describe('CrisisBadge', () => {
  let component: CrisisBadge;
  let fixture: ComponentFixture<CrisisBadge>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CrisisBadge]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CrisisBadge);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
