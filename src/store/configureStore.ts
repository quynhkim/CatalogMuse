import { configureStore } from "@reduxjs/toolkit";
import type { Middleware } from "@reduxjs/toolkit";
import { persistReducer, persistStore } from "redux-persist";
import { createLogger } from "redux-logger";
import rootReducer from "./rootReducer";
import { persistConfig } from "./persistConfig";

export function createAppStore() {
  const persistedReducer = persistReducer(persistConfig, rootReducer);
  const logger = createLogger() as Middleware;

  const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) => {
      const middleware = getDefaultMiddleware({ serializableCheck: false });
      if (import.meta.env.DEV) {
        return middleware.concat(logger);
      }
      return middleware;
    },
  });

  const persistor = persistStore(store);

  return { store, persistor };
}

type StoreType = ReturnType<typeof createAppStore>["store"];

export type RootState = ReturnType<StoreType["getState"]>;
export type AppDispatch = StoreType["dispatch"];
