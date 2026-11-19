import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/shell/app-layout/app-layout.component';
import { NotFoundComponent } from './pages/other-page/not-found/not-found.component';
import { HomeComponent } from './pages/home/home.component';
import { ImportsPageComponent } from './pages/datasets/imports/imports-page.component';
import { DbIngestPageComponent } from './pages/datasets/db-ingest/db-ingest-page.component';
import { IndexPageComponent } from './pages/datasets/index/index-page.component';
import { LakehousePageComponent } from './pages/datasets/lakehouse/lakehouse-page.component';
import { SyncSecretsPageComponent } from './pages/operations/sync-secrets-page.component';
import { AppEndpointsPageComponent } from './pages/catalog/app-endpoints-page.component';

export const routes: Routes = [
  {
    path: '',
    component: AppLayoutComponent,
    children: [
      {
        path: '',
        component: HomeComponent,
        pathMatch: 'full',
        title: 'Consumer Complaints Administration',
      },
      {
        path: 'datasets',
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'imports' },
          {
            path: 'imports',
            component: ImportsPageComponent,
            title: 'Imports | Consumer Complaints Administration',
          },
          {
            path: 'db-ingest',
            component: DbIngestPageComponent,
            title: 'DB Ingest | Consumer Complaints Administration',
          },
          {
            path: 'index',
            component: IndexPageComponent,
            title: 'Vector Stores | Consumer Complaints Administration',
          },
          {
            path: 'lakehouse',
            component: LakehousePageComponent,
            title: 'Lakehouse | Consumer Complaints Administration',
          },
        ],
      },
      {
        path: 'app-endpoints',
        component: AppEndpointsPageComponent,
        title: 'App Endpoints | Consumer Complaints Administration',
      },
      {
        path: 'operations',
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'sync-secrets' },
          {
            path: 'sync-secrets',
            component: SyncSecretsPageComponent,
            title: 'Sync secrets | Consumer Complaints Administration',
          },
        ],
      },
    ],
  },
  {
    path: '**',
    component: NotFoundComponent,
    title: 'Not found | Consumer Complaints Administration',
  },
];
