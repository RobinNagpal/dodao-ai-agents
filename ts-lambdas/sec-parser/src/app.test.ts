import supertest from 'supertest';

import {app} from './app';

describe('Express app', () => {
  describe('Routing', () => {
    it.only('should return `Hello world` when GET index', async () => {
      const response = await supertest(app).post('/latest-ten-q-parsed').send({
        latestTenQUrl: "https://www.sec.gov/Archives/edgar/data/1988494/000095017024127114/fvr-20240930.htm"
      });

      expect(response.statusCode).toEqual(200);
      expect(response.body.msg).toEqual('Hello World');
    });

    it('should return `NOT FOUND` when GET a not found route', async () => {
      const response = await supertest(app).get('/random-page');

      expect(response.statusCode).toEqual(404);
      expect(response.body.error).toEqual('NOT FOUND');
    });
  });
});
