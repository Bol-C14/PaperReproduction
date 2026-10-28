; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x77 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a)))))
(let ((?x90 (bvmul ((_ extract 15 0) ((_ extract 15 0) (ite (bvslt ?x77 (_ bv0 16)) (bvneg ?x77) ?x77))) ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))))))))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65532 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv0 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let (($x30 (and (distinct ?x20 (_ bv0 1)) true)))
(let ((?x24 (bvmul ((_ extract 15 0) (ite (bvslt a (_ bv0 16)) (bvneg a) a)) ((_ zero_extend 13) ((_ extract 2 0) b)))))
(and (distinct (ite $x30 ?x24 c) (ite $x30 ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) ?x90)))) c)) true))))))))
(check-sat)
