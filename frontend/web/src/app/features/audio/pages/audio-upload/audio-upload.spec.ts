import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AudioUpload } from './audio-upload';

describe('AudioUpload', () => {
  let component: AudioUpload;
  let fixture: ComponentFixture<AudioUpload>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AudioUpload]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AudioUpload);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
