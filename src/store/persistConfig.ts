import type { PersistConfig, Storage } from "redux-persist";
import type { RootReducer } from "./rootReducer";

const storage: Storage = {
  getItem: (key) => Promise.resolve(window.localStorage.getItem(key)),
  setItem: (key, value) => {
    window.localStorage.setItem(key, value);
    return Promise.resolve();
  },
  removeItem: (key) => {
    window.localStorage.removeItem(key);
    return Promise.resolve();
  },
};

export const persistConfig: PersistConfig<RootReducer> = {
  key: "catalog-muse",
  storage,
  whitelist: ["appState"],
};
