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

package it.polito.dbdmg.searum.rules;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.WritableComparable;
import org.apache.hadoop.io.WritableComparator;

/**
 * custom writable comparator to sort rule by (conclusion,lift). First by
 * conclusion and for the same value of the conclusion sort by lift.
 * 
 */
public class RulesWritableComparator extends WritableComparator {

    protected RulesWritableComparator() {
        super(Text.class, true); // true to create instances
    }

    @Override
    public int compare(WritableComparable a, WritableComparable b) {
        String[] splitA = a.toString().split("#");
        String firstKeyA = splitA[0].trim();
        Double secondaryKeyA = new Double(splitA[1].trim());

        String[] splitB = b.toString().split("#");
        String firstKeyB = splitB[0].trim();
        Double secondaryKeyB = new Double(splitB[1].trim());

        if (firstKeyA.compareTo(firstKeyB) == 0) {
            return (-1) * secondaryKeyA.compareTo(secondaryKeyB);
        }

        return (-1) * firstKeyA.compareTo(firstKeyB);
    }

}
