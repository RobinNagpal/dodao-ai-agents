import 'express-async-errors';
import {main} from "@/parser";

import express, { json } from 'express';
import helmet from 'helmet';

const app = express();
app.use(json());
app.use(helmet());


app.get('/', async (_, res) => {
  await main();
  res.json({
    msg: 'Hello World',
  });
});

app.use((_, res, _2) => {
  res.status(404).json({ error: 'NOT FOUND' });
});

export { app };
