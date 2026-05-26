import { TestBed } from '@angular/core/testing';

import { Rlhf } from './rlhf';

describe('Rlhf', () => {
  let service: Rlhf;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Rlhf);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
