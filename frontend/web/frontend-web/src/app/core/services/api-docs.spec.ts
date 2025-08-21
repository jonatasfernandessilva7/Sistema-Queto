import { TestBed } from '@angular/core/testing';

import { ApiDocs } from './api-docs';

describe('ApiDocs', () => {
  let service: ApiDocs;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ApiDocs);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
