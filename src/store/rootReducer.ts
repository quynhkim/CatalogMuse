import { combineReducers } from "@reduxjs/toolkit";
import appReducer from "@/containers/App/appSlice";

const rootReducer = combineReducers({
  appState: appReducer,
});

export default rootReducer;
export type RootReducer = ReturnType<typeof rootReducer>;
