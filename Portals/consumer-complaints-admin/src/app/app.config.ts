import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { Directionality } from '@angular/cdk/bidi';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { LiveDirectionality } from './core/services/live-directionality.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(),
    { provide: Directionality, useClass: LiveDirectionality },
  ],
};
