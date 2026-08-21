// Auto-generated benchmark data & interactive graph slice
window.BENCHMARK_DATA = {
  "arangodb": {
    "platform_key": "arangodb",
    "platform_name": "ArangoDB",
    "load": {
      "wall_clock_seconds": 17.48,
      "nodes_loaded": 74062,
      "relationships_loaded": 150000,
      "nodes_per_second": 4236.5,
      "relationships_per_second": 8580.4,
      "method": "ArangoDB import_bulk (1000 docs/batch)"
    },
    "traversals": {
      "1_hop": {
        "p50_ms": 50.0301499851048,
        "p95_ms": 62.26892502454575,
        "mean_ms": 51.82531799946446,
        "iterations": 100,
        "errors": 0
      },
      "2_hop": {
        "p50_ms": 64.04549999570008,
        "p95_ms": 116.24339999543736,
        "mean_ms": 69.08890200254973,
        "iterations": 100,
        "errors": 0
      },
      "3_hop": {
        "p50_ms": 1289.925899996888,
        "p95_ms": 6629.929245005769,
        "mean_ms": 1960.8905600011349,
        "iterations": 100,
        "errors": 0
      }
    },
    "lookups": {
      "point_lookup": {
        "p50_ms": 50.05094999796711,
        "p95_ms": 59.51836001186166,
        "mean_ms": 50.53071299887961,
        "iterations": 100,
        "errors": 0
      },
      "filtered_lookup": {
        "p50_ms": 50.38369999965653,
        "p95_ms": 61.51171501114732,
        "mean_ms": 52.06874199968297,
        "iterations": 100,
        "errors": 0
      }
    },
    "aggregations": {
      "group_by_community": {
        "p50_ms": 1911.7086999904132,
        "p95_ms": 2434.7204299876466,
        "mean_ms": 1949.4479550007964,
        "iterations": 100,
        "errors": 0
      }
    },
    "mixed_workload": {
      "concurrency_1": {
        "queries_per_second": 19.0,
        "duration_seconds": 60,
        "total_queries": 1140,
        "errors": 0,
        "concurrency": 1
      },
      "concurrency_10": {
        "queries_per_second": 180.08333333333334,
        "duration_seconds": 60,
        "total_queries": 10805,
        "errors": 2,
        "concurrency": 10
      },
      "concurrency_40": {
        "queries_per_second": 397.78333333333336,
        "duration_seconds": 60,
        "total_queries": 23867,
        "errors": 0,
        "concurrency": 40
      }
    },
    "footprint": {
      "stored_data_size": "74,062 vertices, 150,000 edges",
      "memory_usage": "not observable (community edition)",
      "instance_specs": "Docker 0.5 vCPU / 256 MB (see docker-compose.yml)",
      "notes": ""
    },
    "caveats": [],
    "cold_start_ms": 67.27
  },
  "cognodb": {
    "platform_key": "cognodb",
    "platform_name": "CognoDB Cloud",
    "load": {
      "wall_clock_seconds": 80.18,
      "nodes_loaded": 74062,
      "relationships_loaded": 150000,
      "nodes_per_second": 923.7,
      "relationships_per_second": 1870.8,
      "method": "Neo4j Python driver UNWIND batch MERGE (1000 rows/batch)"
    },
    "traversals": {
      "1_hop": {
        "p50_ms": 252.29114999820013,
        "p95_ms": 259.10036002023844,
        "mean_ms": 253.4294159989804,
        "iterations": 100,
        "errors": 0
      },
      "2_hop": {
        "p50_ms": 263.7484499864513,
        "p95_ms": 379.4001150046824,
        "mean_ms": 286.11007000057725,
        "iterations": 100,
        "errors": 0
      },
      "3_hop": {
        "p50_ms": 2184.123199986061,
        "p95_ms": 6306.8844699912,
        "mean_ms": 2847.2189565174,
        "iterations": 23,
        "errors": 77
      }
    },
    "lookups": {
      "point_lookup": {
        "p50_ms": 243.877649991191,
        "p95_ms": 247.88254999293713,
        "mean_ms": 254.90592083345595,
        "iterations": 96,
        "errors": 4
      },
      "filtered_lookup": {
        "p50_ms": 245.98720000358298,
        "p95_ms": 469.41240500163985,
        "mean_ms": 277.3427850016742,
        "iterations": 100,
        "errors": 0
      }
    },
    "aggregations": {
      "group_by_community": {
        "p50_ms": 2301.1328499997035,
        "p95_ms": 2434.042229989427,
        "mean_ms": 2311.50384599925,
        "iterations": 100,
        "errors": 0
      }
    },
    "mixed_workload": {
      "concurrency_1": {
        "queries_per_second": 4.05,
        "duration_seconds": 60,
        "total_queries": 243,
        "errors": 0,
        "concurrency": 1
      },
      "concurrency_10": {
        "queries_per_second": 39.3,
        "duration_seconds": 60,
        "total_queries": 2358,
        "errors": 0,
        "concurrency": 10
      },
      "concurrency_40": {
        "queries_per_second": 123.56666666666666,
        "duration_seconds": 60,
        "total_queries": 7414,
        "errors": 1318,
        "concurrency": 40
      }
    },
    "footprint": {
      "stored_data_size": "not observable",
      "memory_usage": "not observable",
      "instance_specs": "see config/platforms.yaml",
      "notes": "Couldn't connect to db-e01bc678.bravo.databases.cognodb.com:7687 (resolved to ('136.70.132.96:7687',)):\nFailed to establish connection to ResolvedIPv4Address(('136.70.132.96', 7687)) (reason [WinError 10065] A socket operation was attempted to an unreachable host)"
    },
    "caveats": [],
    "cold_start_ms": 312.41
  },
  "falkordb": {
    "platform_key": "falkordb",
    "platform_name": "FalkorDB",
    "load": {
      "wall_clock_seconds": 24.41,
      "nodes_loaded": 74062,
      "relationships_loaded": 150000,
      "nodes_per_second": 3033.7,
      "relationships_per_second": 6144.3,
      "method": "FalkorDB Cypher UNWIND batch (1000 rows/batch)"
    },
    "traversals": {
      "1_hop": {
        "p50_ms": 1.1242000036872923,
        "p95_ms": 2.09475499286782,
        "mean_ms": 1.231542999157682,
        "iterations": 100,
        "errors": 0
      },
      "2_hop": {
        "p50_ms": 3.385200005141087,
        "p95_ms": 14.486674986255784,
        "mean_ms": 5.725164000468794,
        "iterations": 100,
        "errors": 0
      },
      "3_hop": {
        "p50_ms": 218.52740002213977,
        "p95_ms": 834.4093000050634,
        "mean_ms": 295.5031439548123,
        "iterations": 91,
        "errors": 9
      }
    },
    "lookups": {
      "point_lookup": {
        "p50_ms": 1.4584000164177269,
        "p95_ms": 3.9499849983258146,
        "mean_ms": 1.7971759993815795,
        "iterations": 100,
        "errors": 0
      },
      "filtered_lookup": {
        "p50_ms": 1.7626999906497076,
        "p95_ms": 9.0484049913357,
        "mean_ms": 2.8812939996714704,
        "iterations": 100,
        "errors": 0
      }
    },
    "aggregations": {
      "group_by_community": {
        "p50_ms": 686.1950999882538,
        "p95_ms": 824.5894349995069,
        "mean_ms": 678.5976870002924,
        "iterations": 100,
        "errors": 0
      }
    },
    "mixed_workload": {
      "concurrency_1": {
        "queries_per_second": 377.3666666666667,
        "duration_seconds": 60,
        "total_queries": 22642,
        "errors": 0,
        "concurrency": 1
      },
      "concurrency_10": {
        "queries_per_second": 1094.45,
        "duration_seconds": 60,
        "total_queries": 65667,
        "errors": 0,
        "concurrency": 10
      },
      "concurrency_40": {
        "queries_per_second": 967.75,
        "duration_seconds": 60,
        "total_queries": 58065,
        "errors": 78,
        "concurrency": 40
      }
    },
    "footprint": {
      "stored_data_size": "74,062 nodes, 150,000 relationships",
      "memory_usage": "31.49M",
      "instance_specs": "Docker 0.5 vCPU / 256 MB (see docker-compose.yml)",
      "notes": ""
    },
    "caveats": [],
    "cold_start_ms": 6.95
  },
  "memgraph": {
    "platform_key": "memgraph",
    "platform_name": "Memgraph",
    "load": {
      "wall_clock_seconds": 9.77,
      "nodes_loaded": 74062,
      "relationships_loaded": 150000,
      "nodes_per_second": 7581.6,
      "relationships_per_second": 15355.2,
      "method": "Neo4j Python driver UNWIND batch MERGE (1000 rows/batch)"
    },
    "traversals": {
      "1_hop": {
        "p50_ms": 2.508350007701665,
        "p95_ms": 4.893945016374346,
        "mean_ms": 2.6704549984424375,
        "iterations": 100,
        "errors": 0
      },
      "2_hop": {
        "p50_ms": 4.667700006393716,
        "p95_ms": 16.644324982189566,
        "mean_ms": 7.267866998736281,
        "iterations": 100,
        "errors": 0
      },
      "3_hop": {
        "p50_ms": 86.20869999867864,
        "p95_ms": 401.05893001309596,
        "mean_ms": 119.98410600004718,
        "iterations": 100,
        "errors": 0
      }
    },
    "lookups": {
      "point_lookup": {
        "p50_ms": 0.9272500028600916,
        "p95_ms": 2.336560006369836,
        "mean_ms": 1.131004999333527,
        "iterations": 100,
        "errors": 0
      },
      "filtered_lookup": {
        "p50_ms": 1.47570000262931,
        "p95_ms": 2.358044986613095,
        "mean_ms": 1.571169999660924,
        "iterations": 100,
        "errors": 0
      }
    },
    "aggregations": {
      "group_by_community": {
        "p50_ms": 290.0164000020595,
        "p95_ms": 371.05621499649715,
        "mean_ms": 281.4343310004915,
        "iterations": 100,
        "errors": 0
      }
    },
    "mixed_workload": {
      "concurrency_1": {
        "queries_per_second": 363.15,
        "duration_seconds": 60,
        "total_queries": 21789,
        "errors": 0,
        "concurrency": 1
      },
      "concurrency_10": {
        "queries_per_second": 889.1,
        "duration_seconds": 60,
        "total_queries": 53346,
        "errors": 1,
        "concurrency": 10
      },
      "concurrency_40": {
        "queries_per_second": 1087.0666666666666,
        "duration_seconds": 60,
        "total_queries": 65224,
        "errors": 4,
        "concurrency": 40
      }
    },
    "footprint": {
      "stored_data_size": "74,062 nodes, 150,000 relationships (logical)",
      "memory_usage": "capped at 256 MB via docker compose",
      "instance_specs": "see config/platforms.yaml",
      "notes": "Cloud consoles may expose additional metrics."
    },
    "caveats": [],
    "cold_start_ms": 42.01
  },
  "neo4j": {
    "platform_key": "neo4j",
    "platform_name": "Neo4j Aura Free",
    "load": {
      "wall_clock_seconds": 24.47,
      "nodes_loaded": 74062,
      "relationships_loaded": 150000,
      "nodes_per_second": 3026.9,
      "relationships_per_second": 6130.4,
      "method": "Neo4j Python driver UNWIND batch MERGE (1000 rows/batch)"
    },
    "traversals": {
      "1_hop": {
        "p50_ms": 52.111549986875616,
        "p95_ms": 60.988370003178716,
        "mean_ms": 53.57697299972642,
        "iterations": 100,
        "errors": 0
      },
      "2_hop": {
        "p50_ms": 52.80574997595977,
        "p95_ms": 58.91054998501203,
        "mean_ms": 54.160120997112244,
        "iterations": 100,
        "errors": 0
      },
      "3_hop": {
        "p50_ms": 70.79180001164787,
        "p95_ms": 100.57094501680695,
        "mean_ms": 73.10543399886228,
        "iterations": 100,
        "errors": 0
      }
    },
    "lookups": {
      "point_lookup": {
        "p50_ms": 51.309600021340884,
        "p95_ms": 101.07128000963712,
        "mean_ms": 56.003048000857234,
        "iterations": 100,
        "errors": 0
      },
      "filtered_lookup": {
        "p50_ms": 102.02925000339746,
        "p95_ms": 163.8151800099874,
        "mean_ms": 126.99414399889065,
        "iterations": 100,
        "errors": 0
      }
    },
    "aggregations": {
      "group_by_community": {
        "p50_ms": 306.32234999211505,
        "p95_ms": 364.69925000274077,
        "mean_ms": 291.7961830008426,
        "iterations": 100,
        "errors": 0
      }
    },
    "mixed_workload": {
      "concurrency_1": {
        "queries_per_second": 12.266666666666667,
        "duration_seconds": 60,
        "total_queries": 736,
        "errors": 0,
        "concurrency": 1
      },
      "concurrency_10": {
        "queries_per_second": 167.26666666666668,
        "duration_seconds": 60,
        "total_queries": 10036,
        "errors": 0,
        "concurrency": 10
      },
      "concurrency_40": {
        "queries_per_second": 607.6333333333333,
        "duration_seconds": 60,
        "total_queries": 36458,
        "errors": 0,
        "concurrency": 40
      }
    },
    "footprint": {
      "stored_data_size": "74,062 nodes, 150,000 relationships (logical)",
      "memory_usage": "not observable (managed cloud)",
      "instance_specs": "see config/platforms.yaml",
      "notes": "Cloud consoles may expose additional metrics."
    },
    "caveats": [],
    "cold_start_ms": 70.19
  }
};
window.GRAPH_SAMPLE = {
  nodes: [{"id": 1, "community": 5}, {"id": 2, "community": 9}, {"id": 3, "community": 0}, {"id": 4, "community": 0}, {"id": 5, "community": 5}, {"id": 6, "community": 1}, {"id": 7, "community": 8}, {"id": 8, "community": 1}, {"id": 9, "community": 7}, {"id": 10, "community": 6}, {"id": 11, "community": 6}, {"id": 12, "community": 0}, {"id": 13, "community": 9}, {"id": 14, "community": 4}, {"id": 15, "community": 1}, {"id": 16, "community": 4}, {"id": 18, "community": 4}, {"id": 19, "community": 0}, {"id": 20, "community": 5}, {"id": 21, "community": 8}, {"id": 22, "community": 2}, {"id": 23, "community": 1}, {"id": 24, "community": 0}, {"id": 25, "community": 1}, {"id": 26, "community": 7}, {"id": 27, "community": 0}, {"id": 28, "community": 8}, {"id": 29, "community": 8}, {"id": 30, "community": 5}, {"id": 31, "community": 1}, {"id": 32, "community": 9}, {"id": 33, "community": 8}, {"id": 34, "community": 9}, {"id": 35, "community": 8}, {"id": 36, "community": 7}, {"id": 37, "community": 4}, {"id": 38, "community": 1}, {"id": 39, "community": 0}, {"id": 40, "community": 8}, {"id": 41, "community": 1}, {"id": 42, "community": 8}, {"id": 43, "community": 8}, {"id": 44, "community": 7}, {"id": 45, "community": 4}, {"id": 46, "community": 3}, {"id": 47, "community": 6}, {"id": 48, "community": 7}, {"id": 49, "community": 5}, {"id": 50, "community": 7}, {"id": 51, "community": 9}, {"id": 52, "community": 4}, {"id": 53, "community": 3}, {"id": 54, "community": 3}, {"id": 55, "community": 1}, {"id": 56, "community": 0}, {"id": 57, "community": 8}, {"id": 58, "community": 0}, {"id": 59, "community": 8}, {"id": 60, "community": 5}, {"id": 61, "community": 6}, {"id": 62, "community": 0}, {"id": 63, "community": 1}, {"id": 64, "community": 6}, {"id": 65, "community": 4}, {"id": 66, "community": 8}, {"id": 67, "community": 1}, {"id": 68, "community": 6}, {"id": 69, "community": 6}, {"id": 70, "community": 3}, {"id": 71, "community": 5}, {"id": 72, "community": 7}, {"id": 73, "community": 8}, {"id": 74, "community": 7}, {"id": 75, "community": 5}, {"id": 76, "community": 9}, {"id": 77, "community": 5}, {"id": 78, "community": 7}, {"id": 79, "community": 1}, {"id": 80, "community": 9}, {"id": 81, "community": 4}, {"id": 82, "community": 3}, {"id": 83, "community": 1}, {"id": 84, "community": 5}, {"id": 85, "community": 7}, {"id": 86, "community": 5}, {"id": 87, "community": 3}, {"id": 88, "community": 6}, {"id": 89, "community": 6}, {"id": 90, "community": 6}, {"id": 91, "community": 5}, {"id": 92, "community": 2}, {"id": 93, "community": 8}, {"id": 94, "community": 4}, {"id": 95, "community": 4}, {"id": 96, "community": 6}, {"id": 97, "community": 4}, {"id": 98, "community": 0}, {"id": 99, "community": 1}, {"id": 100, "community": 8}, {"id": 101, "community": 2}, {"id": 102, "community": 7}, {"id": 103, "community": 0}, {"id": 104, "community": 0}, {"id": 105, "community": 4}, {"id": 106, "community": 5}, {"id": 107, "community": 6}, {"id": 108, "community": 0}, {"id": 109, "community": 7}, {"id": 110, "community": 2}, {"id": 111, "community": 5}, {"id": 112, "community": 8}, {"id": 113, "community": 2}, {"id": 114, "community": 6}, {"id": 115, "community": 4}, {"id": 116, "community": 1}, {"id": 117, "community": 1}, {"id": 118, "community": 0}, {"id": 119, "community": 9}, {"id": 120, "community": 2}, {"id": 121, "community": 0}, {"id": 122, "community": 7}, {"id": 123, "community": 8}, {"id": 124, "community": 8}, {"id": 125, "community": 6}, {"id": 126, "community": 6}, {"id": 127, "community": 2}, {"id": 128, "community": 8}, {"id": 129, "community": 7}, {"id": 130, "community": 1}, {"id": 131, "community": 0}, {"id": 132, "community": 8}, {"id": 133, "community": 3}, {"id": 134, "community": 6}, {"id": 135, "community": 4}, {"id": 136, "community": 4}, {"id": 137, "community": 6}, {"id": 138, "community": 3}, {"id": 139, "community": 7}, {"id": 140, "community": 0}, {"id": 141, "community": 9}],
  edges: [{"source": 1, "target": 13}, {"source": 1, "target": 11}, {"source": 1, "target": 6}, {"source": 1, "target": 3}, {"source": 1, "target": 4}, {"source": 1, "target": 5}, {"source": 1, "target": 15}, {"source": 1, "target": 14}, {"source": 1, "target": 7}, {"source": 1, "target": 8}, {"source": 1, "target": 12}, {"source": 1, "target": 9}, {"source": 1, "target": 10}, {"source": 1, "target": 16}, {"source": 2, "target": 1}, {"source": 2, "target": 18}, {"source": 2, "target": 19}, {"source": 2, "target": 20}, {"source": 2, "target": 21}, {"source": 2, "target": 22}, {"source": 2, "target": 23}, {"source": 2, "target": 24}, {"source": 2, "target": 25}, {"source": 2, "target": 26}, {"source": 2, "target": 27}, {"source": 2, "target": 28}, {"source": 2, "target": 29}, {"source": 2, "target": 30}, {"source": 2, "target": 31}, {"source": 2, "target": 32}, {"source": 2, "target": 33}, {"source": 2, "target": 34}, {"source": 2, "target": 35}, {"source": 2, "target": 36}, {"source": 2, "target": 37}, {"source": 2, "target": 38}, {"source": 2, "target": 39}, {"source": 2, "target": 40}, {"source": 2, "target": 41}, {"source": 2, "target": 42}, {"source": 2, "target": 43}, {"source": 2, "target": 44}, {"source": 2, "target": 45}, {"source": 2, "target": 46}, {"source": 2, "target": 47}, {"source": 2, "target": 48}, {"source": 2, "target": 49}, {"source": 2, "target": 50}, {"source": 2, "target": 51}, {"source": 2, "target": 52}, {"source": 2, "target": 53}, {"source": 2, "target": 54}, {"source": 2, "target": 55}, {"source": 2, "target": 56}, {"source": 2, "target": 57}, {"source": 2, "target": 58}, {"source": 2, "target": 16}, {"source": 2, "target": 59}, {"source": 2, "target": 60}, {"source": 2, "target": 61}, {"source": 2, "target": 62}, {"source": 2, "target": 63}, {"source": 2, "target": 64}, {"source": 2, "target": 65}, {"source": 2, "target": 66}, {"source": 2, "target": 67}, {"source": 2, "target": 68}, {"source": 2, "target": 69}, {"source": 2, "target": 70}, {"source": 2, "target": 71}, {"source": 2, "target": 72}, {"source": 2, "target": 73}, {"source": 2, "target": 74}, {"source": 2, "target": 75}, {"source": 2, "target": 76}, {"source": 2, "target": 77}, {"source": 2, "target": 78}, {"source": 2, "target": 79}, {"source": 2, "target": 80}, {"source": 2, "target": 81}, {"source": 2, "target": 82}, {"source": 2, "target": 83}, {"source": 2, "target": 84}, {"source": 2, "target": 85}, {"source": 2, "target": 86}, {"source": 2, "target": 87}, {"source": 2, "target": 88}, {"source": 2, "target": 89}, {"source": 2, "target": 90}, {"source": 2, "target": 91}, {"source": 2, "target": 92}, {"source": 2, "target": 93}, {"source": 2, "target": 94}, {"source": 2, "target": 95}, {"source": 2, "target": 96}, {"source": 2, "target": 97}, {"source": 2, "target": 98}, {"source": 2, "target": 99}, {"source": 2, "target": 100}, {"source": 2, "target": 101}, {"source": 2, "target": 102}, {"source": 2, "target": 103}, {"source": 2, "target": 104}, {"source": 2, "target": 105}, {"source": 2, "target": 106}, {"source": 2, "target": 107}, {"source": 2, "target": 108}, {"source": 2, "target": 109}, {"source": 2, "target": 110}, {"source": 2, "target": 111}, {"source": 2, "target": 112}, {"source": 2, "target": 113}, {"source": 2, "target": 114}, {"source": 2, "target": 115}, {"source": 2, "target": 116}, {"source": 2, "target": 117}, {"source": 2, "target": 118}, {"source": 2, "target": 119}, {"source": 2, "target": 120}, {"source": 2, "target": 121}, {"source": 2, "target": 122}, {"source": 2, "target": 123}, {"source": 2, "target": 124}, {"source": 2, "target": 125}, {"source": 2, "target": 126}, {"source": 2, "target": 127}, {"source": 2, "target": 128}, {"source": 2, "target": 129}, {"source": 2, "target": 130}, {"source": 2, "target": 131}, {"source": 2, "target": 132}, {"source": 2, "target": 133}, {"source": 2, "target": 134}, {"source": 2, "target": 135}, {"source": 2, "target": 136}, {"source": 2, "target": 137}, {"source": 2, "target": 138}, {"source": 2, "target": 139}, {"source": 2, "target": 140}, {"source": 2, "target": 141}]
};
