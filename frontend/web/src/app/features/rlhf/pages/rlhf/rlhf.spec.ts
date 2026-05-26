import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Rlhf } from './rlhf';

describe('Rlhf', () => {
  let component: Rlhf;
  let fixture: ComponentFixture<Rlhf>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [Rlhf]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Rlhf);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
