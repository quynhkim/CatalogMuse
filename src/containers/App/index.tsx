import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";
import { BrowserRouter, Navigate, Route, Routes, useParams } from "react-router-dom";
import { createAppStore } from "@/store/configureStore";
import { Layout } from "@/components/layout/Layout";
import { CatalogShell, JobDetail, PipelineHome } from "@/containers/CatalogMuse";

const { store, persistor } = createAppStore();

function JobDetailRoute() {
  const { jobId } = useParams();
  return <JobDetail key={jobId} />;
}

function App() {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route element={<CatalogShell />}>
                <Route path="/" element={<PipelineHome />} />
                <Route path="/jobs/:jobId" element={<JobDetailRoute />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Routes>
          </Layout>
        </BrowserRouter>
      </PersistGate>
    </Provider>
  );
}

export default App;
