import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/layout/Navbar";
import apiService from "../api/apiService";
import styles from "./FleetPage.module.css";

const FleetCard: React.FC<{ machineId: string }> = ({ machineId }) => {
  return (
    <Link to={`/machine/${machineId}`} className={styles.card}>
      <div className={styles.cardHead}>
        <h3 className={styles.cardTitle}>{machineId}</h3>
        <span className={styles.pill}>Active</span>
      </div>

      <p className={styles.cardSub}>
        Status: <span className={styles.strong}>Operational</span>
      </p>

      <div className={styles.cardAction}>
        <span>View Dashboard</span>
        <svg
          className={styles.chevron}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
      </div>
    </Link>
  );
};

const FleetPage: React.FC = () => {
  const [allMachines, setAllMachines] = useState<string[]>([]);
  const [displayedMachines, setDisplayedMachines] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchMachines = async () => {
      setLoading(true);

      try {
        const response = await apiService.get("/machines/");
        const machineIds = response.data.map((m: any) => m.machine_id);
        machineIds.sort();

        setAllMachines(machineIds);
        setDisplayedMachines(machineIds.slice(0, 4));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchMachines();
  }, []);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setSearchTerm(term);

    if (!term.trim()) {
      setDisplayedMachines(allMachines.slice(0, 4));
    } else {
      setDisplayedMachines(
        allMachines.filter((id) =>
          id.toLowerCase().includes(term.toLowerCase())
        )
      );
    }
  };

  return (
    <div className={styles.appRoot}>
      <Navbar />

      {/* ------------ TOP HERO SECTION ------------ */}
      <header className={styles.hero}>
        <div className={styles.heroInner}>
          <h2>Machine Fleet Overview</h2>
          <p>
            Monitor real-time health and historical failure risks for all {" "}
            <strong>{allMachines.length}</strong> units in your facility.
          </p>
        </div>
      </header>

      <main className={styles.main}>
        {/* ------------ SEARCH BAR (MOVED LOWER) ------------ */}
        <div className={styles.controlsContainer}>
          <div className={styles.searchWrap}>
            <div className={styles.magWrap}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>

            <input
              type="text"
              placeholder="Search machines by ID..."
              list="machine-datalist"
              className={styles.searchInput}
              value={searchTerm}
              onChange={handleSearch}
            />

            <datalist id="machine-datalist">
              {allMachines.map((id) => (
                <option key={id} value={id} />
              ))}
            </datalist>
          </div>

          <div className={styles.controlsRight}>
            <span className={styles.count}>
              Showing <strong>{displayedMachines.length}</strong> of {" "}
              <strong>{allMachines.length}</strong>
            </span>

            <button
              className={`${styles.btn} ${styles.secondary}`}
              onClick={() => {
                setSearchTerm("");
                setDisplayedMachines(allMachines.slice(0, 4));
              }}
            >
              Clear
            </button>

            {searchTerm === "" && displayedMachines.length < allMachines.length && (
              <button
                className={`${styles.btn} ${styles.primary}`}
                onClick={() => setDisplayedMachines(allMachines)}
              >
                Load All
              </button>
            )}
          </div>
        </div>

        {/* ------------ MACHINE GRID ------------ */}
        <section className={styles.grid}>
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className={styles.skeleton} />
            ))
          ) : displayedMachines.length ? (
            displayedMachines.map((id) => <FleetCard key={id} machineId={id} />)
          ) : (
            <div className={styles.empty}>
              <p>
                No machines found matching <strong>{searchTerm}</strong>
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default FleetPage;
