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
 * custom grouping writable comparator to send to the same reducer all the
 * values of a single natural key, with a single call.
 * 
 */
public class RulesGroupingWritableComparator extends WritableComparator {

    protected RulesGroupingWritableComparator() {
        super(Text.class, true); // true to create instances
    }

    @Override
    public int compare(WritableComparable a, WritableComparable b) {
        String[] splitA = a.toString().split("#");
        String firstKeyA = splitA[0].trim();

        String[] splitB = b.toString().split("#");
        String firstKeyB = splitB[0].trim();

        return firstKeyA.compareTo(firstKeyB);
    }

}
