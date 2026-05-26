import { ComponentFixture, TestBed } from '@angular/core/testing';

import { GaugeChart } from './gauge-chart';

describe('GaugeChart', () => {
  let component: GaugeChart;
  let fixture: ComponentFixture<GaugeChart>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [GaugeChart]
    })
    .compileComponents();

    fixture = TestBed.createComponent(GaugeChart);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
