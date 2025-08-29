import { TestBed } from '@angular/core/testing';

import { ApiAudio } from './api-audio';

describe('ApiAudio', () => {
  let service: ApiAudio;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ApiAudio);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
