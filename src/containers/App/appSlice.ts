import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface AppState {
  sidebarOpen: boolean;
}

const initialState: AppState = {
  sidebarOpen: true,
};

const appStateSlice = createSlice({
  name: "appState",
  initialState,
  reducers: {
    setSidebarOpen(state, action: PayloadAction<boolean>) {
      state.sidebarOpen = action.payload;
    },
  },
});

export const { setSidebarOpen } = appStateSlice.actions;
export default appStateSlice.reducer;
