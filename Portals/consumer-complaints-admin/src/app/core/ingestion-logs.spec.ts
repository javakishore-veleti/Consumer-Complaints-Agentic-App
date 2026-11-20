import { INGESTION_LOG_PAGE_SIZE, INGESTION_LOG_ZONES } from './ingestion-logs';

describe('ingestion-logs', () => {
  it('exposes five zones and page size 30', () => {
    expect(INGESTION_LOG_ZONES.map((z) => z.zone)).toEqual([
      'raw',
      'refined',
      'curated',
      'taxonomy',
      'chroma',
    ]);
    expect(INGESTION_LOG_PAGE_SIZE).toBe(30);
  });
});
