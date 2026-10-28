; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x160 ((_ extract 7 0) ((_ extract 7 0) a))))
(let ((?x151 (bvmul ((_ extract 7 0) ((_ extract 7 0) (ite (bvslt ?x160 (_ bv0 8)) (bvneg ?x160) ?x160))) ((_ zero_extend 5) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b))))))))
(let (($x19 (and (distinct (ite (= (ite (bvsgt (_ bv252 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x21 (ite (and (and (distinct (ite (bvsgt (_ bv0 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x19) (_ bv1 1) (_ bv0 1))))
(let (($x33 (and (distinct ?x21 (_ bv0 1)) true)))
(let ((?x34 (bvmul ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a)) ((_ zero_extend 5) ((_ extract 2 0) b)))))
(and (distinct (ite $x33 ?x34 c) (ite $x33 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x151))))) c)) true))))))))
(check-sat)
