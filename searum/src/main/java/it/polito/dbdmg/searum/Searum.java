/**
 * Copyright 2014 Luigi Grimaudo (grimaudo.luigi@gmail.com)
 * 
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package it.polito.dbdmg.searum;

import java.io.IOException;
import org.apache.mahout.common.Parameters;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Execute the MapReduce algorithm with the given parameter.
 * 
 * @author Luigi Grimaudo
 * @version 0.0.1
 */
public final class Searum {

    private static final Logger log = LoggerFactory.getLogger(Searum.class);
    private static final int ARG_LEN = 5;
    private static final Integer maxHeapSize = 10000;
    private static final Integer numGroups = 1000;

    public static void main(String[] args) throws ClassNotFoundException,
            IOException, InterruptedException {
        if (args.length < ARG_LEN) {
            System.err
                    .println("Usage: Searum <input_file> <output_directory> <discretize (true|false)> <min_sup (0.0|1.0)> [<min_confidence (0.0|1.0)>]");
            System.exit(-1);
        }

        /* Setting Parameters */
        String input = args[1];
        String output = args[2];
        Integer enableDiscretization = (args[3].equals("true")) ? 1 : 0;
        Integer enableRules;
        Double minSupport = new Double(args[4]);
        Double minConfidence = null;
        System.err.println(ARG_LEN);
        if (args.length == (ARG_LEN + 1)) {
            enableRules = new Integer(1);
            minConfidence = new Double(args[5]);
        } else {
            enableRules = new Integer(0);
        }

        String splitPattern = "[\\ ]";

        Parameters params = new Parameters();
        params.set("minSupport", minSupport.toString());
        if (enableRules.compareTo(new Integer(1)) == 0) {
            params.set("minConfidence", minConfidence.toString());
        }
        params.set("splitPattern", splitPattern);
        params.set("input", input);
        params.set("output", output);
        params.set("enableDiscretization", enableDiscretization.toString());
        params.set("enableRules", enableRules.toString());
        params.set("maxHeapSize", maxHeapSize.toString());
        params.set("numGroups", numGroups.toString());

        log.info("========================| SEARUM |=======================");
        log.info("=== A cloud-based Service for Association RUle Mining ===");
        log.info("============== Developed by Luigi Grimaudo ==============");
        log.info("Input file: " + input);
        log.info("Output directory: " + output);
        log.info("MinSupp: " + minSupport.toString());
        if (enableRules.compareTo(new Integer(1)) == 0) {
            log.info("MinConf: " + minConfidence.toString());
        }

        ARM.runPFPGrowth(params);
    }
}
